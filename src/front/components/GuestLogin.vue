<template>
  <div>
    <v-text-field
      label='nickname'
      v-model='nickname'
      clearable
      counter
      maxlength='10'
      color='grey'
    ></v-text-field>
    <v-btn
      color='success'
      :disabled='!nickname'
      @click='send_to_room_browser'
    >
      browse rooms
    </v-btn>
  </div>
</template>

<script>
import router from '../router';

export default {
  name: 'guest_login',

  data () {
    return {
      // will be able to choose server eventually...
      server: 'US-West'
    }
  },

  computed: {

    nickname: {
      get () {
        return this.$store.state.nickname
      },

      set (nickname) {
        this.$store.commit('set_nickname', {'nickname': nickname})
      }
    }
  },

  methods: {
    send_to_room_browser () {
      router.push({
        name: 'room browser',
        params: {
          rbnsp: `/room_browser-${this.server}`
        }
      })
    }
  }
}
</script>

<style scoped> 
.v-btn {
  text-transform: lowercase !important;
}
</style>
