<template>
  <v-card class='pa-0 ma-0'>
    <v-card-title wrap>
      <v-icon
        left
        small
        :color='"red"'
      >
        fa-circle
      </v-icon>
      {{ this.name }}
    </v-card-title>

    <v-card-text class='pa-0 ma-0'>
      cards: {{ this.cards_remaining }}
      <br>
      time: 
        <countdown
          :time='this.time'
        >
          <template slot-scope="props">{{ props.seconds }}</template>
        </countdown>
    </v-card-text>

    <!-- <v-card-actions>
      <v-layout
        align-center
        justify-start
      >
        cards: {{ this.cards_remaining }}
      </v-layout>
      <v-layout
        align-center
        justify-end
      >
        time: 
        <countdown
          :time='this.time'
        >
          <template slot-scope="props">{{ props.seconds }}</template>
        </countdown>
      </v-layout>
    </v-card-actions> -->
  </v-card>
</template>

<script>
export default {
  props: {
    namespace: String,
    spot: Number
  },
  computed: {
    name () {
      return this.$store.state[this.namespace].names[this.spot]
    },

    cards_remaining () {
      return this.$store.state[this.namespace].cards_remaining[this.spot]
    },

    time () {
      return this.$store.state[this.namespace].times[this.spot]
    }
  }
}
</script>
