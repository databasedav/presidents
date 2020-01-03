<template>
  <v-btn class="hand" :style="selected_style" @click="try_select">
    <Card v-for="card in cards" :key="card.id" :card="card.value"></Card>
  </v-btn>
</template>

<script>
import Card from "./Card.vue";
import { mapGetters } from "vuex";

export default {
  name: "Hand",
  components: {
    Card
  },
  props: {
    cards: Array[Number],
    selected: Boolean
  },
  computed: {
    selected_style() {
      return {
        borderColor: this.selected ? "red" : "black"
      };
    }
  },
  methods: {
    try_select() {
      this.$socket.emit("hand click", {
        cards: this.cards.map(card => card.value)
      });
    }
  }
};
</script>

<style scoped>
.unselectable {
  height: auto;
  width: auto;
  margin: 2px;
  padding: 0px;
  padding-left: 10px;
  padding-right: 10px;
  min-width: 0;
  font-size: 15px;
}
v-btn.hand {
  text-align: center;
  text-decoration: none;
  display: inline-block;
  background: none;
  border: 2px solid;
  border-radius: 4px;
  font-size: 10px;
  margin: 2px;
  position: relative;
}
</style>
