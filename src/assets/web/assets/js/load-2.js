function lmRevealAll() {
    lmHideObj = document.getElementById("hide-all");
    lmHideObj.addEventListener("animationend", function() {lmHideObj.remove();}, true);
    if (lmCheckedThemeSwitch) {document.getElementById("lmtheme").setAttribute("checked", "");}
}

lmRevealAll();
