document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("login-form");
  const googleBtn = document.getElementById("google-sign");
  const homeUrl = (window.APP_ROUTES && window.APP_ROUTES.homeUrl) || "/";

  const passwordInput = document.getElementById("login-password");
  const toggleBtn = document.getElementById("toggle-password");
  const toggleIcon = document.getElementById("toggle-password-icon");

  toggleBtn.addEventListener("click", () => {
    const showing = passwordInput.type === "text";
    passwordInput.type = showing ? "password" : "text";
    toggleIcon.classList.toggle("fa-eye", showing);
    toggleIcon.classList.toggle("fa-eye-slash", !showing);
    toggleBtn.setAttribute("aria-label", showing ? "Show password" : "Hide password");
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!form.reportValidity()) {
      return;
    }

    const submitBtn = document.getElementById("input-signin");
    const originalLabel = submitBtn.value;
    submitBtn.disabled = true;
    submitBtn.value = "Signing in...";

    try {
      const response = await fetch(form.action, {
        method: "POST",
        body: new FormData(form),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        alert(data.message || "Invalid email or password.");
        return;
      }

      alert(data.message || "Signed in successfully.");
      window.location.href = data.redirect || homeUrl;
    } catch (err) {
      alert("Could not reach the server. Please check your connection and try again.");
    } finally {
      submitBtn.disabled = false;
      submitBtn.value = originalLabel;
    }
  });

  googleBtn.addEventListener("click", () => {
    window.location.href = "/auth/google";
  });
});
