<template>
  <!-- this swiper is a vertical swiper that swipes through combos + currently
  selected options, where each combo is a swiper that swipes through stored hands -->
  <swiper> </swiper>
</template>

<script>
// TODO: implementing this will only be feasible (for me) after
//       Vue adds supports for reactive maps
// looks like the following:
// long bar that u can swipe up down left and right on
// swiping up and down scrolls thru the combos in order but cycling
//  one of the "combos" is also a list of all the stored hands that have
//  cards that are currently selected, they will be highlighted red
//  as will the copy of the stored hand in the approp. combo's list
// swipping left and right scrolls thru the stored hands of the
//  the given cycle, in power order, but cycling
// delete button to the right of the bar to enable removal from storage
import VueAwesomeSwiper from "vue-awesome-swiper";
import "swiper/dist/css/swiper.css";
//

import { mapGetters } from "vuex";
import StoredHand from "./StoredHand.vue";

export default {
  name: "StoredHandBox",
  components: {
    StoredHand
  },
  // mounted () {
  //   // dynamically add magicscoll dependencies
  //   // css
  //   let link = document.createElement('link')
  //   link.setAttribute('type', 'text/css')
  //   link.setAttribute('rel', 'stylesheet')
  //   link.setAttribute('href', '/magicscroll/magicscroll.css')
  //   link.setAttribute('async', true)
  //   document.head.appendChild(link)
  //   // jsd
  //   link = document.createElement('script')
  //   link.setAttribute('type', 'text/javascript')
  //   link.setAttribute('src', '/magicscroll/magicscroll.js')
  //   link.setAttribute('async', true)
  //   document.head.appendChild(link)

  // },
  props: {
    cards: Array[Number]
  },
  data() {
    return {};
  },
  computed: {
    // ...mapGetters(['stored_hands'])
  },
  methods: {}
};
</script>

<style scoped></style>
