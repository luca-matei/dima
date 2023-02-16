document.documentElement.classList.add("js");
document.documentElement.classList.remove("no-js");

window.addEventListener("load", function() {hideObj.style.animationName = "hide-all";}, true);

let cookie, checked;
let cookies = document.cookie;
if (cookies) {
    cookies = cookies.split(';');
    for (let i=0; i<cookies.length; i++) {
        cookie = cookies[i].split('=');
        if (cookie[0].trim() == '__Host-Theme' && cookie[1] == '2') {
            document.documentElement.setAttribute("data-theme", '2');
            checked = true;
        }
    }
}
