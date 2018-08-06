<template>
  <button
    class='hand'
    :style='selected_style'
    @click='try_select'
  >
    <Card
      v-for='card in cards'
      :class='{unselectable: true}'
      :key='card.id'
      :card='card.value'
      :is_selected='false'
      :functional='false'
    ></Card>
  </button>
</template>

<script>
import Card from './Card.vue'
import { mapGetters } from 'vuex';

export default {
  name: 'Hand',
  components: {
    Card
  },
  props: {
    cards: Array[Number],
    is_selected: Boolean
  },
  data () {
    return {
    }
  },
  computed: {
    selected_style () {
      return {
        borderColor: this.is_selected ? 'red' : 'black'
      }
    }
  },
  methods: {
    try_select () {
      this.$socket.emit('hand click', {'cards': this.cards.map(card => card.value)})
    }
  }
}
</script>

<style scoped>
button.hand {
  text-align: center;
  text-decoration: none;
  display: inline-block;
  background: none;
  border: 2px solid;
  border-radius: 4px;
  font-size: 10px;
  margin: 2px;
  position: relative;
}
</style>