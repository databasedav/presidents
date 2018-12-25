<template>
  <div>
    <TradingOptions
      v-if='trading && asker'
      @ask='$emit("ask", $event)'
    >
    </TradingOptions>

    <v-btn
      v-if='!play_unlocked'
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
      @click="$emit('play')"
      color='success'
    >
      {{ alt_play_button_str }}
    </v-btn>

    <v-btn
      v-if='play_unlocked'
      @click="$emit('play')"
      color='success'
    >
      play
    </v-btn>

    <v-btn
      v-if='play_unlocked'
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
    play_unlocked () {
      return this.$store.state[this.namespace].play_unlocked
    },

    asker () {
      return this.$store.state[this.namespace].asker
    }
  }
}
</script>
