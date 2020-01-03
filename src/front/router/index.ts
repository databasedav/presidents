import Vue from 'vue'
import VueRouter from 'vue-router'
import Home from '../views/Home.vue'
import serverBrowser from "../views/ServerBrowser.vue";
import Presidents from "../views/Presidents.vue";
import Tester from "../views/Tester.vue";


Vue.use(VueRouter)

const routes = [
  {
    path: "/",
    name: "home",
    component: Tester
  },
  {
    path: "/server_browser",
    name: "server browser",
    component: serverBrowser,
    props: true
  },
  // {
  //   path: '/statistics',
  //   name: 'statistics',
  //   component: Statistics
  // },
  {
    path: "/presidents",
    name: "presidents",
    component: Presidents,
    props: true
  },
  {
    path: "/tester",
    name: "tester",
    component: Tester
  },
  {
    path: '/about',
    name: 'about',
    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () => import(/* webpackChunkName: "about" */ '../views/About.vue')
  }
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})

export default router
