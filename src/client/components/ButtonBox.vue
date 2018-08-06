<template>
  <div>
    <button @click='deal_cards'>deal cards</button><br>
    <button @click='store_current_hand'>store current hand</button>
  </div>
</template>

<script>
export default {
  name: 'ButtonBox',
  methods: {
    deal_cards () {
      this.$socket.emit('deal cards')
    },
    store_current_hand () {
      this.$socket.emit('store current hand')
    }
  }
}
</script>
