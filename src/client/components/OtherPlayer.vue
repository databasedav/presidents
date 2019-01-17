<template>
  <v-card>
    <v-card-title>
      <v-icon
        left
        :color='"red"'
      >
        fa-circle
      </v-icon>
    </v-card-title>

    <v-card-text>
      {{ this.name }}
    </v-card-text>

    <v-card-actions>
      <v-layout
        align-center
        justify-start
      >
        {{ this.cards_remaining }}
      </v-layout>
      <v-layout
        align-center
        justify-end
      >
        {{ this.time }}
      </v-layout>
    </v-card-actions>
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
