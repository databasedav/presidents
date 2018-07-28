<template>
  <div>
    <input v-model.number='card_to_add' placeholder='card'>
    <button @click='add_card'>add card</button>
    <Card
      v-for='card in cards'
      :key='card'
      :card='card'
    ></Card>
  </div>
</template>

<script>
import Card from './Card.vue'

export default {
  name: 'CardBox',
  components: {
    Card
  },
  data () {
    return {
      spot: 0,
      card_to_add: ''
    }
  },
  computed: {
    cards () {
      return this.$store.getters.cards_in_spot(this.spot)
    }
  },
  methods: {
    add_card () {
      this.$store.commit({
        type: 'add_card_to_spot',
        spot: this.spot,
        card: this.card_to_add
      })
    }
  }
}
</script>
