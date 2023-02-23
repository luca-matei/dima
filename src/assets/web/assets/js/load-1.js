
// Enables animations and other JS dependent CSS classes
document.documentElement.classList.add("js");
document.documentElement.classList.remove("no-js");

// Get everything ready before displaying it
window.addEventListener("load", function() {hideObj.style.animationName = "hide-all";}, true);

// Set theme from cookies
let lmCheckedThemeSwitch = false;
function lmSetTheme() {
    let cookie, checked;
    let cookies = document.cookie;
    if (cookies) {
        cookies = cookies.split(';');
        for (let i=0; i<cookies.length; i++) {
            cookie = cookies[i].split('=');
            if (cookie[0].trim() == '__Host-Theme' && cookie[1] == '2') {
                document.documentElement.setAttribute("data-theme", '2');
                lmCheckedThemeSwitch = true;
            }
        }
    }
}

lmSetTheme();
