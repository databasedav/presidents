<template>
  <div>
    <TradingOptions
      v-if='trading && asker'
      :namespace='this.namespace'
      @asking_click='$emit("asking_click", $event)'
    >
    </TradingOptions>

    <v-btn
      v-if='!unlocked'
      @click="$emit('unlock')"
      color='error'
    >
      unlock
    </v-btn>

    <v-btn
      v-else
      @click="$emit('lock')"
      color='error'
    >
      lock
    </v-btn>

    <v-btn
      color='info'
    >
      store hand
    </v-btn>

    <v-btn
      @click="$emit('pass')"
      color='warning'
    >
      pass
    </v-btn>

    <v-btn
      v-if='trading && asker'
      @click="$emit(alt_play_button_str)"
      color='success'
    >
      {{ alt_play_button_str }}
    </v-btn>

    <v-btn
      v-else-if='unlocked'
      @click="$emit('play')"
      color='success'
    >
      play
    </v-btn>

    <v-btn
      v-else
      :disabled='true'
      color='success'
    >
      play
    </v-btn>

    <br>
    <button @click="$emit('restart')">restart</button>
  </div>
</template>

<script>
import io from 'socket.io-client'
import TradingOptions from './TradingOptions.vue'

import { namespaced_getter } from '../utils/utils'

export default {
  name: 'ButtonBox',

  props: {
    namespace: String
  },

  components: {
    TradingOptions
  },

  computed: {
    unlocked () {
      return this.$store.state[this.namespace].unlocked
    },

    asker () {
      return this.$store.state[this.namespace].asker
    },

    trading () {
      return this.$store.state[this.namespace].trading
    },

    alt_play_button_str () {
      return this.$store.getters[`${this.namespace}/alt_play_button_str`]
    }
  }
}
</script>
