<template>
  <div>
    <Hand
      v-for='(hand, index) in stored_hands'
      :key='index'
      :cards='hand.cards'
      :is_selected='hand.is_selected'
    ></Hand>
  </div>
</template>

<script>
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
    ...mapGetters(['stored_hands'])
  },
  methods: {
  }
}
</script>

<style scoped>

</style>