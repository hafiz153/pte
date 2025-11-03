document.addEventListener("DOMContentLoaded", () => {
  const sentenceElement = document.getElementById("sentence");
  const startRecordingButton = document.getElementById("startRecording");
  const stopRecordingButton = document.getElementById("stopRecording");
  const scoreElement = document.getElementById("score");
  const explanationElement = document.getElementById("explanation");
  const loadingIndicator = document.getElementById("loading_indicator");
  const contentScoreElement = document.getElementById("content_score");
  const pronunciationScoreElement = document.getElementById(
    "pronunciation_score"
  );
  const fluencyScoreElement = document.getElementById("fluency_score");
  const prevSentenceButton = document.getElementById("prevSentence");
  const nextSentenceButton = document.getElementById("nextSentence");
  const currentSentenceNumberElement = document.getElementById(
    "current_sentence_number"
  );
  const totalSentencesElement = document.getElementById("total_sentences");

  let mediaRecorder;
  let audioChunks = [];
  let currentSentenceIndex = 1; // Start with the first sentence
  let totalSentences = 0; // Initialize totalSentences to 0
  const audioPlayer = document.getElementById("audioPlayer");
  const playAudioButton = document.getElementById("playAudio");

  // Function to fetch total sentences from the backend
  async function fetchTotalSentences() {
    try {
      const response = await fetch("/total_sentences");
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      totalSentences = data.total_sentences;
      totalSentencesElement.textContent = totalSentences;
    } catch (error) {
      console.error("Error fetching total sentences:", error);
      totalSentencesElement.textContent = "N/A";
    }
  }

  async function fetchAndDisplaySentence(sentenceId) {
    console.log(`Fetching sentence ${sentenceId}. Total sentences: ${totalSentences}`);
    try {
      // Ensure totalSentences is fetched before proceeding
      if (totalSentences === 0) {
        await fetchTotalSentences();
      }

      console.log(`Attempting to fetch sentence with ID: ${sentenceId}`);
      console.log(`Current total sentences: ${totalSentences}`);
      const response = await fetch(`/get_sentence/${sentenceId}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      if (data.error) {
        sentenceElement.textContent = data.error;
        // prevSentenceButton.disabled = true;
        // nextSentenceButton.disabled = true;
        // playAudioButton.disabled = true;
        return;
      }
      sentenceElement.textContent = data.text;
      currentSentenceNumberElement.textContent = sentenceId;

      // Generate and load audio (temporarily commented out for debugging)
      // console.log(`Fetching audio from: /generate_audio/${sentenceId}`);
      // const audioResponse = await fetch(`/generate_audio/${sentenceId}`);
      // console.log(`Audio response status: ${audioResponse.status}`);
      // if (!audioResponse.ok) {
      //   throw new Error(`HTTP error! status: ${audioResponse.status}`);
      // }
      // const audioBlob = await audioResponse.blob();
      // const audioUrl = URL.createObjectURL(audioBlob);
      // audioPlayer.src = audioUrl;
      // audioPlayer.style.display = "block";
      playAudioButton.disabled = false;
      prevSentenceButton.disabled = false;
      nextSentenceButton.disabled = false;

      // Enable/disable navigation buttons
      // prevSentenceButton.disabled = sentenceId <= 1;
      // nextSentenceButton.disabled = sentenceId >= totalSentences;
    } catch (error) {
      console.error("Error fetching sentence or generating audio:", error);
      sentenceElement.textContent = "Failed to load sentence.";
      // prevSentenceButton.disabled = true;
      // nextSentenceButton.disabled = true;
      // playAudioButton.disabled = true;
    }
  }

  // Initial load of the first sentence and total sentences
  fetchTotalSentences();
  fetchAndDisplaySentence(currentSentenceIndex);

  playAudioButton.addEventListener("click", () => {
    audioPlayer.play();
  });

  prevSentenceButton.addEventListener("click", () => {
    if (currentSentenceIndex > 1) {
      currentSentenceIndex--;
      fetchAndDisplaySentence(currentSentenceIndex);
    }
  });

  nextSentenceButton.addEventListener("click", () => {
    if (currentSentenceIndex < totalSentences) {
      currentSentenceIndex++;
      fetchAndDisplaySentence(currentSentenceIndex);
    }
  });

  startRecordingButton.addEventListener("click", async () => {
    explanationElement.textContent = ""; // Clear previous explanation
    scoreElement.textContent = "N/A";
    contentScoreElement.textContent = "N/A";
    pronunciationScoreElement.textContent = "N/A";
    fluencyScoreElement.textContent = "N/A";
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.start();
    startRecordingButton.disabled = true;
    stopRecordingButton.disabled = false;
    audioChunks = [];

    mediaRecorder.addEventListener("dataavailable", (event) => {
      audioChunks.push(event.data);
    });

    mediaRecorder.addEventListener("stop", async () => {
      loadingIndicator.style.display = "block"; // Show loading indicator
      const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
      const formData = new FormData();
      formData.append("audio", audioBlob);
      formData.append("sentence", sentenceElement.textContent);

      // Send audio to backend for scoring
      const response = await fetch("/score", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      loadingIndicator.style.display = "none"; // Hide loading indicator
      const pronunciationScoreElement = document.getElementById(
        "pronunciation_score"
      );
      const fluencyScoreElement = document.getElementById("fluency_score");
      const vocabularyScoreElement =
        document.getElementById("vocabulary_score");
      const grammarScoreElement = document.getElementById("grammar_score");

      scoreElement.textContent = data.score;
      const aiResponseJson = data.ai_response;
      contentScoreElement.textContent = aiResponseJson.content;
      pronunciationScoreElement.textContent = aiResponseJson.pronunciation;
      fluencyScoreElement.textContent = aiResponseJson.fluency;

      // Format the AI explanation for better display
      let formattedExplanation = "";
      const lines = aiResponseJson.explanation.split("\n");
      let inList = false;

      lines.forEach((line) => {
        if (line.startsWith("*")) {
          if (!inList) {
            formattedExplanation += "<ul>";
            inList = true;
          }
          formattedExplanation += `<li>${line.substring(1).trim()}</li>`;
        } else {
          if (inList) {
            formattedExplanation += "</ul>";
            inList = false;
          }
          if (line.trim() !== "") {
            formattedExplanation += `<p>${line.trim()}</p>`;
          }
        }
      });

      if (inList) {
        formattedExplanation += "</ul>";
      }

      explanationElement.innerHTML = formattedExplanation;

      startRecordingButton.disabled = false;
      stopRecordingButton.disabled = true;
    });
  });

  stopRecordingButton.addEventListener("click", () => {
    mediaRecorder.stop();
  });
});
