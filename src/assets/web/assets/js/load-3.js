//import * as lm from '/commons/js/app.js';
//window.lm = lm;

const $ = query => document.querySelector(query);

// TODO: lmCrsl, lmSlides

// UTILS

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


// TOP BUTTON

class lmTopBtn {
  constructor() {
    this.scroll = $('#page-scroll');
    this.btn = $('#top-btn');
    this.check();
  }

  check() {
    this.btn.className = this.scroll.scrollTop < this.scroll.offsetHeight ? 'out' : 'in';
  }

}

let topBtn = new lmTopBtn();


// COOKIES

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

  getCookie() {
    return Object.fromEntries(document.cookie.split(';').map(cookie => cookie.split('=')));
  }

  setCookie(key, value) {
    if (key == '__Host-Consent' || this.getCookie[key]) {
      document.cookie = `${key}=${value};Path=/;SameSite=Strict;Secure;${document.cookie}`;
      if (key == '__Host-Consent') {
        this.setCookie('__Host-Theme', $('html').getAttribute('data-theme'));
        this.hideNotice();
      }
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


// SETTINGS

class lmSettings {
  toggleTheme() {
    let theme = $('html').getAttribute('data-theme') || 1;
    let newTheme = theme == 2 ? 1 : 2;

    cookies.setCookie('__Host-Theme', newTheme);
    $('html').setAttribute('data-theme', newTheme);

    if (newTheme == 2) $('#lmtheme').setAttribute('checked', '');
    else $('#lmtheme').removeAttribute('checked');
  }

}

let settings = new lmSettings();


// ANIMATIONS

class lmAnim {
    constructor() {
        this.sensorObj = $('#sensor-cpt');
        this.scrollObj = $('#page-scroll');
        this.buffer = 0.25 * window.innerHeight;

        console.log(this.sensorObj);
        console.log(this.scrollObj);
        console.log(this.buffer);

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

let anim = new lmAnim();


// FORMS

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


document.getElementById("lmid-message-box").addEventListener("click", utils.hideMessage);
document.getElementById("lmid-policy-accept").addEventListener(
    "click", function() {cookies.setCookie('__Host-Consent', 1)});
document.getElementById("lmid-toggle-theme").addEventListener("click", settings.toggleTheme);
document.getElementById("page-scroll").addEventListener("scroll", topBtn.check);

let tmp;
tmp = document.getElementById("lmid-policy-withdraw");
if (tmp) {tmp.addEventListener("click", cookies.withdraw);}
tmp = document.getElementById("lmid-toggle-password");
if (tmp) {tmp.addEventListener("click", forms.togglePassword);}
