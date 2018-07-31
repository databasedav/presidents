<template>
  <div>
    <button @click='deal_cards'>deal cards</button>
  </div>
</template>

<script>
export default {
  name: 'ButtonBox',
  methods: {
    deal_cards () {
      this.$socket.emit('deal cards')
    }
  }
}
</script>
