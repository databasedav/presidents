import Vue from 'vue'
import VueRouter from 'vue-router'
import Home from '../views/Home.vue'
import Login from "../views/Login.vue"
import GameBrowser from "../views/GameBrowser.vue";
import Presidents from "../views/Presidents.vue";
import Tester from "../views/Tester.vue";
import Game from "../components/Game.vue"


Vue.use(VueRouter)

const routes = [
  {
    path: "/",
    name: "home",
    component: Login
  },
  {
    path: "/game_browser",
    name: "game browser",
    component: GameBrowser,
  },
  // {
  //   path: '/statistics',
  //   name: 'statistics',
  //   component: Statistics
  // },
  {
    path: "/presidents",
    name: "presidents",
    component: Game,
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
