<template>
  <v-container>
    <v-row justify="center">
      <v-btn
        class="rank"
        v-for="rank in this.asking_options"
        :key="52 + rank"
        :outline="asking_options_selected_arr[rank]"
        :style="
          asking_options_selected_arr[rank]
            ? ''
            : { 'background-color': '#696969' }
        "
        @click="$emit('asking_click', rank)"
      >
        {{ ranks[rank] }}
      </v-btn>
    </v-row>
  </v-container>
</template>

<script>
import Card from "./Card.vue";

export default {
  name: "AskingOptions",

  props: {
    namespace: String
  },

  data() {
    return {
      // TODO: where to put this?
      ranks: [
        null,
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "10",
        "J",
        "Q",
        "K",
        "A",
        "2"
      ]
    };
  },

  computed: {
    asking_options () {
      return this.$store.state[this.namespace].asking_options_arr;
    },

    asking_options_selected_arr () {
      return this.$store.state[this.namespace].asking_options_selected_arr;
    }
  },

  methods: {}
};
</script>

<style scoped>
.v-btn.rank {
  min-width: 0;
  height: 30px;
  width: 30px;
  margin: 4px;
  font-size: 20px;
  text-align: center;
  border-radius: 5px;
}
</style>
