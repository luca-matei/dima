
// Enables animations and other JS dependent CSS classes
document.documentElement.classList.add("js");
document.documentElement.classList.remove("no-js");

let lmHideAllTimeout;
window.addEventListener("DOMContentLoaded", function() {
    // Wait 1 second before displaying hide-all to avoid flashing
    lmHideAllTimeout = setTimeout(function() {
        hideObj.style.display = "flex";
        clearTimeout(lmHideAllTimeout);
    }, 1000);
}, true);

window.addEventListener("load", function() {
    // If page loading took less than 1 sec, avoid displaying hide-all
    let loadTime = window.performance.timing.domContentLoadedEventEnd- window.performance.timing.navigationStart;
    if (loadTime <= 1000) {
        clearTimeout(lmHideAllTimeout);
    } else {
        hideObj.style.animationName = "reveal-all";
    }
}, true);

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
    } else if (document.documentElement.getAttribute("data-theme") == '2') {
        lmCheckedThemeSwitch = true;
    }
}

lmSetTheme();
