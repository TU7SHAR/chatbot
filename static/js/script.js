window.addEventListener("pageshow", function () {
  document.querySelectorAll('button[type="submit"]').forEach((btn) => {
    btn.disabled = false;
    btn.classList.remove("btn-disabled");
  });
});

document.addEventListener("DOMContentLoaded", () => {
  const allForms = document.querySelectorAll("form");

  allForms.forEach((form) => {
    // Skip botPipelineForm — it has its own AJAX submit handler
    if (form.id === "botPipelineForm") return;

    form.addEventListener("submit", function () {
      const submitBtn = this.querySelector('button[type="submit"]');

      if (submitBtn && !submitBtn.disabled) {
        submitBtn.disabled = true;
        submitBtn.classList.add("btn-disabled");

        const oldText = submitBtn.innerText.toUpperCase();

        if (oldText.includes("DELETE") || oldText.includes("BOT")) {
          submitBtn.innerText = "DELETING...";
        } else if (oldText.includes("CREATE") || oldText.includes("BOT")) {
          submitBtn.innerText = "CREATING...";
        } else if (oldText.includes("INITIALIZE")) {
          submitBtn.innerText = "INITIALIZING...";
        } else if (oldText.includes("LOGIN") || oldText.includes("SIGN IN")) {
          submitBtn.innerText = "AUTHENTICATING...";
        } else if (
          oldText.includes("REGISTER") ||
          oldText.includes("SIGN UP")
        ) {
          submitBtn.innerText = "CREATING ACCOUNT...";
        } else if (oldText.includes("UPLOAD") || oldText.includes("TRAIN")) {
          submitBtn.innerText = "UPLOADING...";
        } else if (oldText.includes("DECRYPT") || oldText.includes("UNLOCK")) {
          submitBtn.innerText = "DECRYPTING...";
        } else if (oldText.includes("INVITE") || oldText.includes("SEND")) {
          submitBtn.innerText = "SENDING...";
        } else {
          submitBtn.innerText = "PROCESSING...";
        }
      }
    });
  });
});

function copyDecryptionKey(key, event) {
  event.preventDefault();
  const btn = event.target;
  const originalText = btn.innerText;

  const triggerSuccessAnimation = () => {
    btn.innerText = "COPIED!";
    const originalBg = btn.style.background;
    btn.style.background = "#28a745";

    setTimeout(() => {
      btn.innerText = originalText;
      btn.style.background = originalBg;
    }, 2000);
  };

  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard
      .writeText(key)
      .then(triggerSuccessAnimation)
      .catch((err) => console.error("Copy failed", err));
  } else {
    let textArea = document.createElement("textarea");
    textArea.value = key;
    document.body.appendChild(textArea);
    textArea.select();
    try {
      document.execCommand("copy");
      triggerSuccessAnimation();
    } catch (err) {
      console.error("Fallback copy failed", err);
    }
    document.body.removeChild(textArea);
  }
}

async function startScraping(event) {
  event.preventDefault();

  const urlInput = document.getElementById("scrape_url");
  const deepCrawlInput = document.getElementById("use_deep_crawl");
  const btnScrape = document.getElementById("btn-scrape");
  const progressDiv = document.getElementById("scrape-progress");
  const statusText = document.getElementById("scrape-status-text");

  if (!urlInput || !btnScrape || !progressDiv) {
    console.warn("Scraper elements not found on this page.");
    return;
  }

  const targetUrl = urlInput.value.trim();
  const useDeepCrawl = deepCrawlInput ? deepCrawlInput.checked : false;

  if (!targetUrl) return;

  urlInput.disabled = true;
  if (deepCrawlInput) deepCrawlInput.disabled = true;
  btnScrape.disabled = true;
  btnScrape.innerText = "STARTING...";
  progressDiv.style.display = "block";

  if (statusText) {
    statusText.innerText = "SENDING TO ENGINE...";
    statusText.style.color = "var(--text-dark)";
  }

  try {
    const startResponse = await fetch("/admin/api/scrape/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: targetUrl, use_spider: useDeepCrawl }),
    });

    const startData = await startResponse.json();

    if (startData.error) throw new Error(startData.error);

    const jobId = startData.job_id;
    if (statusText) statusText.innerText = "SCRAPING IN PROGRESS...";

    const pollInterval = setInterval(async () => {
      try {
        const cacheBuster = new Date().getTime();
        const statusResponse = await fetch(
          `/admin/api/scrape/status/${jobId}?t=${cacheBuster}`,
        );
        const statusData = await statusResponse.json();

        if (statusData.status === "completed") {
          clearInterval(pollInterval);
          if (statusText) {
            statusText.innerText = "SUCCESS! KNOWLEDGE INGESTED.";
            statusText.style.color = "#28a745";
          }
          setTimeout(() => window.location.reload(), 1500);
        } else if (statusData.status === "failed") {
          clearInterval(pollInterval);
          throw new Error(statusData.error || "Scraping failed.");
        }
      } catch (pollError) {
        clearInterval(pollInterval);
        handleScrapeError(pollError.message);
      }
    }, 3000);
  } catch (error) {
    handleScrapeError(error.message);
  }

  function handleScrapeError(msg) {
    if (statusText) {
      statusText.innerText = "SCRAPE FAILED";
      statusText.style.color = "#d93025";
    }
    alert("Error: " + msg);
    urlInput.disabled = false;
    if (deepCrawlInput) deepCrawlInput.disabled = false;
    btnScrape.disabled = false;
    btnScrape.innerText = "Start Scraping";
  }
}
