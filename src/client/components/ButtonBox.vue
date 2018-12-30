<template>
  <div>
    <AskingOptions
      v-if='trading && asker'
      :namespace='this.namespace'
      @asking_click='$emit("asking_click", $event)'
    >
    </AskingOptions>

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
      :disabled='true'
    >
      store hand
    </v-btn>

    <v-btn
      @click='$emit("pass")'
      color='warning'
    >
      pass
    </v-btn>

    <v-btn
      v-if='trading && asker'
      @click="$emit(alt_play_button_str)"
      :disabled='!unlocked'
      color='success'
    >
      {{ alt_play_button_str }}
    </v-btn>

    <v-btn
      v-else-if='trading && giver'
      @click='$emit("give")'
      :disabled='!unlocked'
      color='success'
    >
      give
    </v-btn>

    <v-btn
      v-else
      @click="$emit('play')"
      :disabled='!unlocked'
      color='success'
    >
      play
    </v-btn>
  </div>
</template>

<script>
import io from 'socket.io-client'
import AskingOptions from './AskingOptions.vue'

import { namespaced_getter } from '../utils/utils'

export default {
  name: 'ButtonBox',

  props: {
    namespace: String
  },

  components: {
    AskingOptions
  },

  computed: {
    unlocked () {
      return this.$store.state[this.namespace].unlocked
    },

    asker () {
      return this.$store.state[this.namespace].asker
    },

    giver () {
      return this.$store.state[this.namespace].giver
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
