// // ===============================
// // 2) MODAL OPEN / CLOSE
// // ===============================
// function toggleModal() {
//   const modal = document.getElementById("loginModal");
//   modal.classList.toggle("active");
// }


// // ===============================
// // 3) SIGN IN ↔ SIGN UP SWITCH
// // ===============================
// function toggleSignup() {
//   const loginFields = document.getElementById("loginFields");
//   const signupFields = document.getElementById("signupFields");
//   const authBtn = document.getElementById("authBtn");
//   const authForm = document.getElementById("authForm");
//   const heading = document.querySelector(".modal-card h2");
//   const subText = document.querySelector(".modal-card p");
//   const footer = document.getElementById("authFooter");

//   const loginInputs = loginFields.querySelectorAll("input");
//   const signupInputs = signupFields.querySelectorAll("input, select");

//   const isSignupMode = signupFields.style.display === "block";

//   if (isSignupMode) {
//     loginFields.style.display = "block";
//     signupFields.style.display = "none";

//     loginInputs.forEach(input => input.disabled = false);
//     signupInputs.forEach(input => input.disabled = true);

//     authBtn.textContent = "Sign In";
//     authForm.action = "/login";

//     heading.textContent = "Welcome Back";
//     subText.textContent = "Sign in to access your digital yearbook";

//     footer.innerHTML =
//       `Don't have an account?
//        <span onclick="toggleSignup()" style="cursor:pointer;">
//          Create one
//        </span>`;
//   } else {
//     loginFields.style.display = "none";
//     signupFields.style.display = "block";

//     loginInputs.forEach(input => input.disabled = true);
//     signupInputs.forEach(input => input.disabled = false);

//     authBtn.textContent = "Create Account";
//     authForm.action = "/signup";

//     heading.textContent = "REQUEST ACCESS";
//     subText.textContent =
//       "Request access to join the digital archive";

//     footer.innerHTML =
//       `Already have an account?
//        <span onclick="toggleSignup()" style="cursor:pointer;">
//          Sign In
//        </span>`;
//   }
// }

// window.onload = function () {
//   const signupInputs = document.querySelectorAll("#signupFields input, #signupFields select");
//   signupInputs.forEach(input => input.disabled = true);
// };