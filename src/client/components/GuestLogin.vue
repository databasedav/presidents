<template>
  <div>
    <v-text-field
    label='nickname'
    v-model='nickname'
    clearable
    counter
    maxlength='20'
    color='grey'
  ></v-text-field>
  <v-btn
    color='success'
    :disabled='!nickname'
    to='/room_browser'
  >
    browse rooms
  </v-btn>
  </div>
</template>

<script>
export default {
  name: 'guest login',

  computed: {
    nickname: {
      get () {
        return this.$store.state.nickname
      },

      set (nickname) {
        this.$store.commit('set_nickname', nickname)
      }
    }
  }
}
</script>

<style>
.v-btn {
  text-transform: lowercase !important;
}
</style>
