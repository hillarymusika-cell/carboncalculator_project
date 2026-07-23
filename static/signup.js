document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("signup-form");
  const password = document.getElementById("login-password");
  const confirmPassword = document.getElementById("confirm-password");
  const mismatchNote = document.getElementById("password-mismatch");
  const googleBtn = document.getElementById("google-sign");
  const homeUrl = (window.APP_ROUTES && window.APP_ROUTES.homeUrl) || "/";

  function wireToggle(inputId, buttonId, iconId) {
    const input = document.getElementById(inputId);
    const button = document.getElementById(buttonId);
    const icon = document.getElementById(iconId);
    if (!input || !button || !icon) return;

    button.addEventListener("click", () => {
      const showing = input.type === "text";
      input.type = showing ? "password" : "text";
      icon.classList.toggle("fa-eye", showing);
      icon.classList.toggle("fa-eye-slash", !showing);
      button.setAttribute("aria-label", showing ? "Show password" : "Hide password");
    });
  }

  wireToggle("login-password", "toggle-password", "toggle-password-icon");
  wireToggle("confirm-password", "toggle-confirm-password", "toggle-confirm-password-icon");

  function checkPasswordsMatch() {
    const mismatch = confirmPassword.value.length > 0 && password.value !== confirmPassword.value;
    mismatchNote.hidden = !mismatch;
    confirmPassword.setCustomValidity(mismatch ? "Passwords do not match" : "");
    return !mismatch;
  }

  password.addEventListener("input", checkPasswordsMatch);
  confirmPassword.addEventListener("input", checkPasswordsMatch);

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!form.reportValidity() || !checkPasswordsMatch()) {
      return;
    }

    const submitBtn = document.getElementById("input-signup");
    const originalLabel = submitBtn.value;
    submitBtn.disabled = true;
    submitBtn.value = "Creating account...";

    try {
      const actionUrl = form.getAttribute("action") || "/auth/signup";
      const response = await fetch(actionUrl, {
        method: "POST",
        body: new FormData(form),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        alert(data.message || "Something went wrong. Please try again.");
        return;
      }

      alert(data.message || "Account created successfully.");
      window.location.href =data.redirect|| homeUrl;
    } catch (err) {
      alert("Could not reach the server. Please check your connection and try again.");
    } finally {
      submitBtn.disabled = false;
      submitBtn.value = originalLabel;
    }
  });

  googleBtn.addEventListener("click", () => {
    alert("Google sign-in isn't set up yet.");
  });
});
