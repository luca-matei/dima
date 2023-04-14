const lm = {

scrollObj: $('#lmid-page-scroll'),

init: function() {
    this.scrollObj.addEventListener("scroll", this.topBtnCheck);
    this.topBtnCheck();
    this.utils.setActive();
    this.anims.init();
    this.cookies.check();

    $("#lmid-message-box").addEventListener("click", lm.utils.hideMessage);
    $("#lmid-policy-accept").addEventListener("click", function() {lm.cookies.setCookie('__Host-Consent', 1)});
    $("#lmid-toggle-theme").addEventListener("click", lm.settings.toggleTheme);

    //$("#lmid-policy-withdraw").addEventListener("click", lm.cookies.withdraw);
    //$("#lmid-toggle-password").addEventListener("click", forms.togglePassword);
},

topBtnCheck: function() {
    let topBtnObj = $('#lmid-top-btn');
    if (lm.scrollObj.scrollTop < lm.scrollObj.offsetHeight) {
        topBtnObj.className = 'lmbtn-out';
    } else {
        topBtnObj.style.display = "";
        topBtnObj.className = 'lmbtn-in';
    }
},

utils: {
    messageDelay: null,
    // Activate navbar links
    setActive: function() {
        let [section, resource] = document.URL.substr(document.baseURI.length).split('/');
        let navs = Array.from(document.querySelectorAll('#lmid-app-header, #lmid-compaside'));
        let links = new Array, res = section ? `${section}/${resource}` : resource;

        for (let nav of navs) links.push(...nav.getElementsByTagName('a'));

        if (!section) section = 'home';
        for (let link of links) {
            let href = link.getAttribute('href');
            if ([section, res].includes(href) && href != 'coming-soon') {
                link.classList.add('lmactive');
            }
        }
    },

    setMessage: function(color, message) {
        let box = $('#lmid-message-box');
        box.textContent = message;
        box.style.display = 'block';
        box.className = `lmbd-${color}`;
        window.clearTimeout(lm.utils.messageDelay);
        lm.utils.messageDelay = window.setTimeout(lm.utils.hideMessage, message.length * 150);
    },

    hideMessage: function() {
        $('#lmid-message-box').style.display = 'none';
    }

},

cookies: {
    noticeObj: $('#lmid-cookies-notice'),

    check: function() {
        if (!lm.cookies.getCookie('__Host-Consent')) {
            lm.cookies.showNotice();
        }
    },

    showNotice: function() {
        lm.cookies.noticeObj.style.display = 'block';
    },

    hideNotice: function() {
        lm.cookies.noticeObj.style.display = 'none';
    },

    getCookie: function(key) {
        let cks = Object.fromEntries(document.cookie.split(';').map(cookie => cookie.split('=')));
        return cks[key]
    },

    setCookie: function(key, value) {
        // If the new cookie is for consent or if the user has consented to the cookies module
        if (key == '__Host-Consent' || lm.cookies.getCookie('__Host-Consent')) {
            document.cookie = `${key}=${value};Path=/;SameSite=Strict;Secure;${document.cookie}`;
            if (key == '__Host-Consent') {
                lm.cookies.setCookie('__Host-Theme', $('html').getAttribute('data-theme'));
                lm.cookies.hideNotice();
            }
        }
    },

    withdraw: function() {
        lm.cookies.showNotice();
        Object.entries(lm.cookies.getCookie()).forEach(([key, value]) => {
            document.cookie = `${key}=${value};max-age=0;path=/;SameSite=Strict;Secure;${document.cookie}`;
        });
    }
},

settings: {
    toggleTheme: function() {
        let theme = $('html').getAttribute('data-theme') || 1;
        let newTheme = theme == 2 ? 1 : 2;

        lm.cookies.setCookie('__Host-Theme', newTheme);
        $('html').setAttribute('data-theme', newTheme);

        if (newTheme == 2) $('#lmid-theme').setAttribute('checked', '');
        else $('#lmid-theme').removeAttribute('checked');
    }
},

anims: {
    sensorObj: $('#lmid-sensor-cpt'),
    cptObjs: document.getElementsByClassName('lmcpt'),

    init: ()=> {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.intersectionRatio >= 0.5) {
                    entry.target.classList.add('lmanim');
                    entry.target.classList.remove('lmcpt');
                    observer.unobserve(entry.target);
                }
            });
        }, { root: document.querySelector("#lmid-page-scroll"), threshold: 0.5});

        const cpts = document.querySelectorAll(".lmcpt");
        cpts.forEach((elem) => {
            observer.observe(elem);
        });
    },
}

}

lm.init();

class lmForms {
  togglePassword() {
    let field = $('#lmid-password');
    let eye = field.nextElementSibling.children[0];

    if (field.getAttribute('type') === 'password') {
      field.setAttribute('type', 'text');
      eye.className = 'fa fa-eye-slash';
    } else {
      field.setAttribute('type', 'password');
      eye.className = 'fa fa-eye';
    }
  }
}
//let forms = new lmForms();
