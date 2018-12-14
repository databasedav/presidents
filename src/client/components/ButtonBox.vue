<template>
  <div>
    <button @click='restart'>restart</button>
    
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
    },

    restart () {
      this.$socket.emit('restart')
    }
  }
}
</script>
