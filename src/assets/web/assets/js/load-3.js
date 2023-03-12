const lm = {

scrollObj: $('#page-scroll'),

init: function() {
    this.scrollObj.addEventListener("scroll", this.topBtnCheck);
    this.topBtnCheck();
    this.anims.init();

    $("#message-box").addEventListener("click", this.utils.hideMessage);
    $("#lmid-policy-accept").addEventListener("click", function() {this.cookies.setCookie('__Host-Consent', 1)});
    $("#lmid-toggle-theme").addEventListener("click", this.settings.toggleTheme);

    //$("#lmid-policy-withdraw").addEventListener("click", lm.cookies.withdraw);
    //$("#lmid-toggle-password").addEventListener("click", forms.togglePassword);
},

topBtnCheck: function() {
    let topBtnObj = $('#top-btn');
    if (lm.scrollObj.scrollTop < lm.scrollObj.offsetHeight) {
        topBtnObj.className = 'out';
    } else {
        topBtnObj.style.display = "";
        topBtnObj.className = 'in';
    }
},

utils: {
    messageDelay: null,
    // Activate navbar links
    setActive: function() {
        let [section, resource] = document.URL.substr(document.baseURI.length).split('/');
        let navs = Array.from(document.querySelectorAll('#app-header, #compaside'));
        let links = new Array, res = section ? `${section}/${resource}` : resource;

        for (let nav of navs) links.push(...nav.getElementsByTagName('a'));

        if (!section) section = 'home';
        for (let link of links) {
            let href = link.getAttribute('href');
            if ([section, res].includes(href) && href != 'coming-soon') {
                link.classList.add('active');
            }
        }
    },

    setMessage: function(color, message) {
        let box = $('#message-box');
        box.textContent = message;
        box.style.display = 'block';
        box.className = `lmbd-${color}`;
        window.clearTimeout(this.messageDelay);
        this.messageDelay = window.setTimeout(this.hideMessage, message.length * 150);
    },

    hideMessage: function() {
        $('#message-box').style.display = 'none';
    }

},

cookies: {
    noticeObj: $('#cookies-notice'),

    check: function() {
        if (!this.getCookie('__Host-Consent')) {
            this.showNotice();
        }
    },

    showNotice: function() {
        this.noticeObj.style.display = 'block';
    },

    hideNotice: function() {
        this.noticeObj.style.display = 'none';
    },

    getCookie: function(key) {
        let cks = Object.fromEntries(document.cookie.split(';').map(cookie => cookie.split('=')));
        return cks[key]
    },

    setCookie: function(key, value) {
        // If the new cookie is for consent or if the user has consented to the cookies module
        if (key == '__Host-Consent' || this.getCookie('__Host-Consent')) {
            document.cookie = `${key}=${value};Path=/;SameSite=Strict;Secure;${document.cookie}`;
            if (key == '__Host-Consent') {
                this.setCookie('__Host-Theme', $('html').getAttribute('data-theme'));
                this.hideNotice();
            }
        }
    },

    withdraw: function() {
        this.showNotice();
        Object.entries(this.getCookie()).forEach(([key, value]) => {
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

        if (newTheme == 2) $('#lmtheme').setAttribute('checked', '');
        else $('#lmtheme').removeAttribute('checked');
    }
},

anims: {
    sensorObj: $('#sensor-cpt'),
    buffer: 0.25 * window.innerHeight,
    cptObjs: $('.cpt'),

    init: function() {
        window.addEventListener('load', this.check, true);
        lm.scrollObj.addEventListener('scroll', this.check);
    },

    check: function() {
        if (!this.cptObjs) {
            lm.scrollObj.removeEventListener('scroll', this.check, true);
        } else {
            let cptObj = this.cptObjs[0];

            if (cptObj.getBoundingClientRect().top < this.sensorObj.getBoundingClientRect().top - buffer) {
                cptObj.classList.add('anim'), cptObj.classList.remove('cpt');
                this.cptObjs = $('.cpt');
                this.check();
            }
        }
    }
}

}

lm.init();

class lmForms {
  togglePassword() {
    let field = $('#lmpassword');
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
