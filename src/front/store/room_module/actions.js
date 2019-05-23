export default {
  emit_card_click (context, payload) {
    this._vm.$socket[context.state.rnsp].emit('card_click', payload)
  },

  emit_unlock (context, payload) {
    this._vm.$socket[context.state.rnsp].emit('unlock')
  },

  emit_lock (context, payload) {
    this._vm.$socket[context.state.rnsp].emit('lock')
  },

  emit_play (context, payload) {
    this._vm.$socket[context.state.rnsp].emit('play')
  },

  emit_unlock_pass (context, payload) {
    this._vm.$socket[context.state.rnsp].emit('unlock_pass')
  },

  emit_pass (context, payload) {
    this._vm.$socket[context.state.rnsp].emit('pass')
  },

  emit_ask (context, payload) {
    this._vm.$socket[context.state.rnsp].emit('ask')
  },

  emit_give (context, payload) {
    this._vm.$socket[context.state.rnsp].emit('give')
  },

  emit_asking_click (context, payload) {
    this._vm.$socket[context.state.rnsp].emit('asking_click', payload)
  }
}