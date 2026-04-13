// ── Page exit transition on link clicks ──
document.querySelectorAll('a').forEach(link => {
  link.addEventListener('click', function (e) {
    const href = this.getAttribute('href');
    if (!href || href.startsWith('#')) return;
    e.preventDefault();
    document.body.classList.add('page-exit');
    setTimeout(() => {
      window.location.href = href;
    }, 700);
  });
});

// ── Modal open / close ──
function toggleModal() {
  document.getElementById("loginModal").classList.toggle("active");
}

// ── Toggle between Sign In and Sign Up ──
function toggleSignup() {
  const login = document.getElementById("loginFields");
  const signup = document.getElementById("signupFields");
  const btn = document.getElementById("authBtn");
  const form = document.getElementById("authForm");
  const heading = document.querySelector(".modal-card h2");
  const sub = document.querySelector(".modal-card p");
  const footer = document.getElementById("authFooter");

  const loginInputs = login.querySelectorAll("input");
  const signupInputs = signup.querySelectorAll("input, select");

  const signupOpen = signup.style.display === "block";

  if (!signupOpen) {
    // OPEN SIGNUP
    login.style.display = "none";
    signup.style.display = "block";

    loginInputs.forEach(input => input.disabled = true);
    signupInputs.forEach(input => input.disabled = false);

    btn.textContent = "Create Account";
    form.action = "/signup";

    heading.textContent = "Create Account";
    sub.textContent = "Complete your details to access the digital archive";

    footer.innerHTML =
      'Already have an account? <span onclick="toggleSignup()" style="cursor:pointer;">Sign In</span>';
  } else {
    // BACK TO LOGIN
    login.style.display = "block";
    signup.style.display = "none";

    loginInputs.forEach(input => input.disabled = false);
    signupInputs.forEach(input => input.disabled = true);

    btn.textContent = "Sign In";
    form.action = "/login";

    heading.textContent = "Welcome Back";
    sub.textContent = "Sign in to access your digital yearbook";

    footer.innerHTML =
    footer.innerHTML =
  'Don\'t have an account? <span onclick="toggleSignup()" style="cursor:pointer;">Create one</span>';
  }
}
window.onload = function () {
  // disable signup fields by default
  const signupInputs = document.querySelectorAll("#signupFields input, #signupFields select");
  signupInputs.forEach(input => input.disabled = true);

  // show flash toast if message exists
  const flash = document.getElementById("flashMessage");
  if (flash) {
    const message = flash.dataset.message;
    showToast(message);
  }
};

// =========================tost=========================

function showToast(message) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.classList.add("show");

  setTimeout(() => {
    toast.classList.remove("show");
  }, 3000);
}


