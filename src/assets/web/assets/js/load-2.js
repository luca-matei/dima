function lmRevealAll() {
    lmHideObj = document.getElementById("lmid-hide-all");
    lmHideObj.addEventListener("animationend", function() {lmHideObj.remove();}, true);
    if (lmCheckedThemeSwitch) {document.getElementById("lmid-theme").setAttribute("checked", "");}
}

lmRevealAll();
