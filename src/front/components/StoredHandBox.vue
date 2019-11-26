<template>
  <div>
    <!-- <Hand
      v-for='(hand, index) in stored_hands'
      :key='index'
      :cards='hand.cards'
      :is_selected='hand.is_selected'
    ></Hand> -->
  </div>
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


import { mapGetters } from 'vuex'
import Hand from './Hand.vue'

export default {
  name: 'StoredHandBox',
  components: {
    Hand
  },
  props: {
    cards: Array[Number]
  },
  data () {
    return {
    }
  },
  computed: {
    // ...mapGetters(['stored_hands'])
  },
  methods: {
  }
}
</script>

<style scoped>

</style>