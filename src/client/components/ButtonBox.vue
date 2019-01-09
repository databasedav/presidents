<template>
  <div>
    <AskingOptions
      v-if='trading && asker'
      :namespace='this.namespace'
      @asking_click='$emit("asking_click", $event)'
    >
    </AskingOptions>

    <!-- <v-btn
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
    </v-btn> -->

    <v-btn
      @click="$emit(lock_unlock_str)"
      color='error'
    >
      {{ lock_unlock_str }}
      <v-icon v-if='!unlocked' small right>fa-lock</v-icon>
      <v-icon v-else small right>fa-unlock</v-icon>
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
      <v-icon right>skip_next</v-icon>
    </v-btn>

    <v-btn
      v-if='trading && asker'
      @click="$emit(alt_play_button_str)"
      :disabled='!unlocked'
      color='success'
    >
      {{ alt_play_button_str }}
      <v-icon v-if='alt_play_button_str === "ask"' small right>fa-question</v-icon>
      <v-icon v-else-if='alt_play_button_str === "give"' small right>fa-gift</v-icon>
      <template v-else>
        <v-icon small right>fa-question</v-icon><v-icon small right>fa-gift</v-icon>
      </template>
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
      <v-icon right>play_arrow</v-icon>
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

    lock_unlock_str () {
      return this.unlocked ? 'lock' : 'unlock'
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

<style scoped>
.v-btn {
  text-transform: lowercase !important;
}
</style>
