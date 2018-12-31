<template>
  <v-container fluid text-xs-center>
    <v-layout align-center justify-center column fill-height>
      <v-flex class='logo' xs12>
        presidents
      </v-flex>
      <v-flex xs4 text-xs-center>
        <GuestLogin/>
      </v-flex>
    </v-layout>
  </v-container>
</template>

<script>
import GuestLogin from '../components/GuestLogin.vue'

export default {
  name: 'home',
  components: {
    GuestLogin
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css?family=Pacifico');

.logo {
  color: black;
  font-family: 'Pacifico', cursive;
  font-size: 25pt
}

.v-btn {
  font-family: 'Pacifico', cursive;
}
</style>
