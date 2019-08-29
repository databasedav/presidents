import 'material-design-icons-iconfont/dist/material-design-icons.css'
import '@fortawesome/fontawesome-free/css/all.css'
import Vue from 'vue'
import App from './App.vue'
import store from './store/store'
import router from './router'
import Vuetify from 'vuetify'
import VueCountdown from '@chenfengyuan/vue-countdown'

import 'vuetify/dist/vuetify.min.css'

Vue.config.productionTip = false

Vue.use(Vuetify);
Vue.component(VueCountdown.name, VueCountdown)

export default new Vue({
  router,
  store,
  render: h => h(App)
}).$mount('#app')
