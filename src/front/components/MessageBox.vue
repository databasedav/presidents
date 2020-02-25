<template>
  <v-row justify="center">
    <v-col cols='11'>
      <ul class="overflow-x-auto" v-chat-scroll="{always:false}" style="height: 15vh">
        <li v-for="message in messages">{{ message }}</li>
      </ul>
    </v-col>
  </v-row>
</template>

<script>

export default {

  props: {
    namespace: String
  },

  computed: {
    messages () {
      return this.$store.state[this.namespace].messages;
    },
  }
};
</script>

<style>
</style>
