(function () {
    const homeSection = document.getElementById("home");
    const entrySection = document.getElementById("entry");
    const continueBtn = document.getElementById("continue");
    const steps = document.querySelectorAll(".step");
    const nextBtn = document.getElementById("next-btn");
    const prevBtn = document.getElementById("prev-btn");
    const submitBtn = document.getElementById("submit-btn");
    const progressSteps = document.querySelectorAll(".progress-step");
    const progressLabels = document.querySelectorAll(".progress-labels span");
    const progressBar = document.getElementById("progress-bar");
    let currentStep = 0;

    continueBtn.addEventListener("click", () => {
        homeSection.style.display = "none";
        entrySection.style.display = "block";
        window.scrollTo({ top: 0, behavior: "smooth" });
    });

    document.querySelectorAll('input[name="transport"]').forEach((el) => {
        el.addEventListener("change", () => {
            const other = document.getElementById("other-transport-container");
            other.style.display = el.value === "other" ? "block" : "none";
        });
    });

    document.querySelectorAll('input[name="frequency"]').forEach((el) => {
        el.addEventListener("change", () => {
            const wrap = document.getElementById("freq-custom-wrap");
            wrap.style.display = el.value === "multiple" ? "block" : "none";
        });
    });

    function updateProgress(n) {
        progressSteps.forEach((s, i) => {
            s.classList.toggle("active", i === n);
            s.classList.toggle("done", i < n);
        });
        progressLabels.forEach((l, i) => {
            l.classList.toggle("active", i === n);
        });
        if (progressBar) progressBar.setAttribute("aria-valuenow", String(n + 1));
    }

    function showStep(n) {
        steps.forEach((step, i) => step.classList.toggle("active", i === n));
        prevBtn.style.display = n > 0 ? "block" : "none";
        nextBtn.style.display = n < steps.length - 1 ? "block" : "none";
        submitBtn.style.display = n === steps.length - 1 ? "block" : "none";
        updateProgress(n);
    }

    nextBtn.addEventListener("click", () => {
        if (currentStep < steps.length - 1) {
            currentStep++;
            showStep(currentStep);
            window.scrollTo({ top: entrySection.offsetTop - 80, behavior: "smooth" });
        }
    });

    prevBtn.addEventListener("click", () => {
        if (currentStep > 0) {
            currentStep--;
            showStep(currentStep);
        }
    });

    submitBtn.addEventListener("click", async (e) => {
        e.preventDefault();
        const form = document.getElementById("carbon-form");
        submitBtn.classList.add("loading");
        submitBtn.textContent = "Calculating…";
        try {
            const response = await fetch("/submit", {
                method: "POST",
                body: new FormData(form),
            });
            if (!response.ok) throw new Error("Server responded with " + response.status);
            await response.json().catch(() => ({}));
            window.location.href = "/dashboard";
        } catch (error) {
            console.error("Error:", error);
            alert("Something went wrong submitting your entry. Please try again.");
        } finally {
            submitBtn.classList.remove("loading");
            submitBtn.textContent = "Submit";
        }
    });
})();

/* —— Real-time preview via /api/calculate —— */
(function () {
  const form = document.getElementById("carbon-form");
  if (!form) return;

  let previewEl = document.getElementById("live-preview");
  if (!previewEl) {
    previewEl = document.createElement("div");
    previewEl.id = "live-preview";
    previewEl.setAttribute("aria-live", "polite");
    previewEl.style.cssText =
      "margin-top:16px;padding:14px 16px;border-radius:12px;" +
      "background:#f0faf7;border:1px solid #c5e8df;color:#004E4F;" +
      "font-size:0.95rem;display:none;";
    const nav = form.querySelector(".nav-buttons");
    if (nav) form.insertBefore(previewEl, nav);
    else form.appendChild(previewEl);
  }

  let timer = null;

  async function runPreview() {
    try {
      const res = await fetch("/api/calculate", {
        method: "POST",
        body: new FormData(form),
      });
      const data = await res.json();
      if (!res.ok || !data.ok) {
        previewEl.style.display = "none";
        return;
      }
      const t = (data.total_t_co2e != null
        ? data.total_t_co2e
        : (data.total_kg_co2e || 0) / 1000
      ).toFixed(3);
      const parts = Object.entries(data.breakdown || {})
        .map(([k, v]) => `${k}: ${(v / 1000).toFixed(3)} t`)
        .join(" · ");
      previewEl.innerHTML =
        `<strong>Live estimate:</strong> ${t} t CO₂e` +
        (parts ? `<br><span style="opacity:.8;font-size:.85rem">${parts}</span>` : "");
      previewEl.style.display = "block";
    } catch (_) {
      previewEl.style.display = "none";
    }
  }

  function schedulePreview() {
    clearTimeout(timer);
    timer = setTimeout(runPreview, 350);
  }

  form.addEventListener("change", schedulePreview);
  form.addEventListener("input", schedulePreview);
})();
