<template>
  <v-toolbar
    class='d-inline-block'
    height='25px'
    color='black'
  >
    <v-icon size='10px' :color='this.dot_color'>fa-circle</v-icon>

    <v-spacer></v-spacer>

    <v-toolbar-title class='ma-1'>{{ this.name }}</v-toolbar-title>

    <v-spacer></v-spacer>

    <v-icon class='ma-1' size='10px'>fa-hashtag</v-icon>
    {{ this.cards_remaining }}

    <v-spacer></v-spacer>

    <v-icon class='ma-1' size='10px'>fa-clock</v-icon>
    <countdown
      ref='turn'
      :time='this.turn_time'
      :transform='transform'
      :auto-start='true'
      :emit-events='false'
    >
      <template slot-scope="props">{{ props.seconds }}</template>
    </countdown>

    <v-spacer></v-spacer>

    <v-icon class='ma-1' size='10px'>fa-clock</v-icon>
    <countdown
      ref='reserve'
      :time='this.reserve_time'
      :transform='transform'
      :auto-start='true'
      :emit-events='false'
    >
      <template slot-scope="props">{{ props.seconds }}</template>
    </countdown>
  </v-toolbar>
</template>

<script>
export default {
  props: {
    namespace: String,
    spot: Number
  },

  methods: {
    transform(props) {
      Object.entries(props).forEach(([key, value]) => {
        // adds leading zero
        const digits = value < 10 ? `0${value}` : value
        props[key] = `${digits}`
      });

      return props;
    }
  },

  // TODO: add watcher for starting and stopping reserve time 

  computed: {
    name () {
      return this.$store.state[this.namespace].names[this.spot]
    },

    cards_remaining () {
      const cards_remaining = this.$store.state[this.namespace].cards_remaining[this.spot]
      return cards_remaining < 10 ? `0${cards_remaining}` : cards_remaining
    },

    turn_time () {
      return this.$store.state[this.namespace].turn_times[this.spot]
    },

    reserve_time () {
      return this.$store.state[this.namespace].reserve_times[this.spot]
    },

    dot_color () {
      return this.$store.state[this.namespace].dot_colors[this.spot]
    },

    turn_time_state () {
      return this.$store.state[this.namespace].turn_time_states[this.spot]
    },

    reserve_time_state () {
      return this.$store.state[this.namespace].reserve_time_states[this.spot]
    },
  },

  watch: {
    turn_time_state (new_val, old_val) {
      if (new_val) {
        console.log(this.$refs.turn)
        this.$refs.turn.start()
      } else {
        this.$refs.turn.abort()
      }
    },
    reserve_time_state (new_val, old_val) {
      if (new_val) {
        this.$refs.reserve.start()
      } else {
        this.$refs.reserve.abort()
      }
    }
  }
}

</script>

<style>
.v-toolbar__content {
  padding: 0 5px !important
}
.v-toolbar__title {
  font-size: 12px !important
}
</style>
