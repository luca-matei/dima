function lmRevealAll() {
    hideObj = document.getElementById("hide-all")
    hideObj.addEventListener("animationend", function() {hideObj.remove();}, true);
    if (lmCheckedThemeSwitch) {document.getElementById("lmtheme").setAttribute("checked", "");}
}

lmRevealAll();
