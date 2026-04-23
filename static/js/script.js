// ── Page exit transition ──
document.querySelectorAll('a').forEach(link => {
  link.addEventListener('click', function (e) {
    const href = this.getAttribute('href');
    if (!href || href.startsWith('#')) return;
    e.preventDefault();
    document.body.classList.add('page-exit');
    setTimeout(() => { window.location.href = href; }, 700);
  });
});

// ── Modal ──
function toggleModal() {
  document.getElementById("loginModal").classList.toggle("active");
}

// ── Toggle Sign In / Sign Up ──
function toggleSignup() {
  const login = document.getElementById("loginFields");
  const signup = document.getElementById("signupFields");
  const btn = document.getElementById("authBtn");
  const heading = document.querySelector(".modal-card h2");
  const sub = document.querySelector(".modal-card p");
  const footer = document.getElementById("authFooter");

  const isSignup = signup.style.display === "block";

  if (!isSignup) {
    login.style.display = "none";
    signup.style.display = "block";
    btn.textContent = "Create Account";
    heading.textContent = "Create Account";
    sub.textContent = "Complete your details to access the digital archive";
    footer.innerHTML = 'Already have an account? <span onclick="toggleSignup()" style="cursor:pointer;">Sign In</span>';
  } else {
    login.style.display = "block";
    signup.style.display = "none";
    btn.textContent = "Sign In";
    heading.textContent = "Welcome Back";
    sub.textContent = "Sign in to access your digital yearbook";
    footer.innerHTML = 'Don\'t have an account? <span onclick="toggleSignup()" style="cursor:pointer;">Create one</span>';
  }
}

// ── Auth form submit ──
document.getElementById("authForm").addEventListener("submit", async function (e) {
  e.preventDefault();

  const isSignup = document.getElementById("signupFields").style.display === "block";

  if (isSignup) {
    const payload = {
      full_name: document.querySelector("#signupFields input[name='full_name']").value,
      email: document.querySelector("#signupFields input[name='signup_email']").value,
      branch: document.querySelector("#signupFields select[name='branch']").value,
      roll_number: document.querySelector("#signupFields input[name='roll']").value,
      password: document.querySelector("#signupFields input[name='signup_password']").value,
    };

    const res = await fetch("/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    showToast(data.message);

    if (data.message && data.message.toLowerCase().includes("success")) {
      setTimeout(() => toggleSignup(), 1500);
    }

  } else {
    const payload = {
      email: document.querySelector("#loginFields input[name='email']").value,
      password: document.querySelector("#loginFields input[name='password']").value,
    };

    const res = await fetch("/signin", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    if (data.success) {
      const btn = document.querySelector(".login-btn");
      btn.textContent = data.name.toUpperCase();
      btn.classList.add("logged-in");
      btn.onclick = null; // disable modal on click, or wire to profile
      toggleModal();
      showToast("Welcome back, " + data.name + "!");
    }
  }
});

// ── Toast ──
function showToast(message) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 3000);
}

// ── On load ──
window.onload = function () {
  const flash = document.getElementById("flashMessage");
  if (flash) showToast(flash.dataset.message);

  fetch("/api/me").then(r => r.json()).then(data => {
    if (data.loggedIn) {
      const btn = document.querySelector(".login-btn");
      btn.textContent = data.name.toUpperCase();
      btn.classList.add("logged-in");
      btn.onclick = null;
    }
  });
};