<template>
  <v-container>
    <v-row justify="center">
      presidents
    </v-row>
    <v-row justify="center">
      <v-col cols="6">
        <v-text-field
          label="username"
          v-model="username"
          clearable
          counter
          maxlength="5"
          color="grey"
        ></v-text-field>
      </v-col>
    </v-row>
    <v-row justify="center">
      <v-btn
        color="success"
        :disabled="!username || username.length > 5"
        @click="send_to_game_browser"
      >
        browse games
      </v-btn>
    </v-row> 
  </v-container>
</template>

<script>
import router from "../router";

export default {
  name: "Login",

  computed: {
    username: {
      get() {
        return this.$store.state.username;
      },

      set(username) {
        this.$store.commit("set_username", { username: username });
      }
    }
  },

  methods: {
    send_to_game_browser () {
      router.push({ name: 'game browser' });
    }
  }
};
</script>

<style scoped>
.v-btn {
  text-transform: lowercase !important;
}
</style>
