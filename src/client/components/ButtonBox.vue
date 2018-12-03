<template>
  <div>
    <button @click='join_game'>join game</button><br>
    <button @click='store_current_hand'>store current hand</button>
  </div>
</template>

<script>
export default {
  name: 'ButtonBox',
  methods: {
    join_game () {
      this.$socket.emit('join game')
    },
    store_current_hand () {
      this.$socket.emit('store current hand')
    }
  }
}
</script>
