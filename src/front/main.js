import "material-design-icons-iconfont/dist/material-design-icons.css";
import "@fortawesome/fontawesome-free/css/all.css";
import Vue from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import vuetify from './plugins/vuetify'
import VueChatScroll from 'vue-chat-scroll'


const VueCountdown = require("@chenfengyuan/vue-countdown")
Vue.component(VueCountdown.name, VueCountdown)
Vue.use(VueChatScroll)

Vue.config.productionTip = false

new Vue({
  router,
  store,
  vuetify,
  render: h => h(App)
}).$mount('#app')
