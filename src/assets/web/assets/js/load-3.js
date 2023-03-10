class lmUtils {
  constructor() {
    this.messageDelay = null;
    this.setActive();
  }

  /*
  getKeys(d) {
    return Object.keys(d);
  }
  */

  // Activate navbar links
  setActive() {
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
  }

  setMessage(color, message) {
    let box = $('#message-box');
    box.textContent = message;
    box.style.display = 'block';
    box.className = `lmbd-${color}`;
    window.clearTimeout(this.messageDelay);
    this.messageDelay = window.setTimeout(this.hideMessage, message.length * 150);
  }

  hideMessage() {
    $('#message-box').style.display = 'none';
  }

}
let utils = new lmUtils();

function lmTopBtnCheck() {
    if ($('#page-scroll').scrollTop < $('#page-scroll').offsetHeight) {
        $('#top-btn').className = 'out';
    } else {
        $('#top-btn').style.display = "";
        $('#top-btn').className = 'in';
    }
}
lmTopBtnCheck();


class lmCookies {
    constructor() {
        if (!this.getCookie('__Host-Consent')) {
            this.showNotice();
        }
    }

    showNotice() {
        $('#cookies-notice').style.display = 'block';
    }

    hideNotice() {
        $('#cookies-notice').style.display = 'none';
    }

    getCookie(key) {
        let cks = Object.fromEntries(document.cookie.split(';').map(cookie => cookie.split('=')));
        return cks[key]
    }

    setCookie(key, value) {
        console.log(key, value);
        document.cookie = `${key}=${value};Path=/;SameSite=Strict;Secure;${document.cookie}`;
        if (key == '__Host-Consent') {
            this.setCookie('__Host-Theme', $('html').getAttribute('data-theme'));
            this.hideNotice();
        }
    }

    withdraw() {
        this.showNotice();
        Object.entries(this.getCookie()).forEach(([key, value]) => {
            document.cookie = `${key}=${value};max-age=0;path=/;SameSite=Strict;Secure;${document.cookie}`;
        });
    }

}
let cookies = new lmCookies();


class lmSettings {
    toggleTheme() {
        let theme = $('html').getAttribute('data-theme') || 1;
        let newTheme = theme == 2 ? 1 : 2;
        console.log(newTheme);

        cookies.setCookie('__Host-Theme', newTheme);
        $('html').setAttribute('data-theme', newTheme);

        if (newTheme == 2) $('#lmtheme').setAttribute('checked', '');
        else $('#lmtheme').removeAttribute('checked');
    }

}
let settings = new lmSettings();


class lmAnim {
    constructor() {
        this.sensorObj = $('#sensor-cpt');
        this.scrollObj = $('#page-scroll');
        this.buffer = 0.25 * window.innerHeight;

        //console.log(this.sensorObj);
        //console.log(this.scrollObj);
        //console.log(this.buffer);

        this.cptObjs = document.querySelectorAll('.cpt');
        window.addEventListener('load', this.check, true);
        this.scrollObj.addEventListener('scroll', this.check);

        console.log(this.cptObjs);
    }

    check() {
        if (!this.cptObjs) {
            this.scrollObj.removeEventListener('scroll', check, true);
        } else {
            cptObj = this.cptObjs[0];

            if (cptObj.getBoundingClientRect().top < this.sensorObj.getBoundingClientRect().top - buffer) {
                cptObj.classList.add('anim'), cptObj.classList.remove('cpt');
                this.cptObjs = document.querySelectorAll('.cpt');
                this.check();
                }
            }
    }
}
//let anim = new lmAnim();


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
let forms = new lmForms();


$("#page-scroll").addEventListener("scroll", lmTopBtnCheck);
$("#lmid-message-box").addEventListener("click", utils.hideMessage);
$("#lmid-policy-accept").addEventListener(
    "click", function() {cookies.setCookie('__Host-Consent', 1)});
$("#lmid-toggle-theme").addEventListener("click", settings.toggleTheme);

let tmp;
tmp = $("#lmid-policy-withdraw");
if (tmp) {tmp.addEventListener("click", cookies.withdraw);}
tmp = $("#lmid-toggle-password");
if (tmp) {tmp.addEventListener("click", forms.togglePassword);}
