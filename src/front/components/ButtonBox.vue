<template>
  <v-container>
    <v-row dense>
      <v-col>
        <AskingOptions
          v-if="trading && asker"
          :namespace="this.namespace"
          @asking_click="$emit('asking_click', $event)"
        >
        </AskingOptions>
      </v-col>
    </v-row>

    <v-row justify="center">
      <!-- lock/unlock button -->
      <v-col :cols="6">
        <v-btn
          @click="$emit(lock_unlock_str)"
          block
          color="error"
          height="70"
        >
          {{ lock_unlock_str }}
          <v-icon v-if="!unlocked" right>fa-lock</v-icon>
          <v-icon v-else right>fa-unlock</v-icon>
        </v-btn>
      </v-col>

      <v-col :cols="6">
        <v-btn
          v-if="trading && asker"
          @click="$emit(alt_play_button_str)"
          block
          :disabled="!unlocked"
          color="success"
          height="70"
        >
          {{ alt_play_button_str }}
          <v-icon v-if="alt_play_button_str === 'ask'" right
            >fa-question</v-icon
          >
          <v-icon v-else-if="alt_play_button_str === 'give'" right
            >fa-gift</v-icon
          >
          <template v-else>
            <v-icon right>fa-question</v-icon><v-icon right>fa-gift</v-icon>
          </template>
        </v-btn>

        <v-btn
          v-else-if="trading && giver"
          @click="$emit('give')"
          block
          :disabled="!unlocked"
          color="success"
          height="70"
        >
          give
          <v-icon right>fa-gift</v-icon>
        </v-btn>

        <v-btn
          v-else
          @click="$emit('play')"
          block
          :disabled="!unlocked"
          color="success"
          height="70"
        >
          play
          <v-icon x-large right>play_arrow</v-icon>
        </v-btn>
      </v-col>

      <v-col :cols="6">
        <v-btn
          color="info"
          block
          :disabled="true"
          height="70"
        >
          store hand
          <br>
          (coming soon)
          <v-icon right>fa-save</v-icon>
        </v-btn>
      </v-col>

      <v-col :cols="6">
        <v-btn
          @click="$emit(pass_button_action)"
          block
          :disabled="trading"
          color="warning"
          height="70"
        >
          pass
          <v-icon v-if="!pass_unlocked" right>fa-lock</v-icon>
          <v-icon v-else x-large right>skip_next</v-icon>
        </v-btn>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import AskingOptions from "./AskingOptions.vue";

export default {
  name: "ButtonBox",

  props: {
    namespace: String
  },

  components: {
    AskingOptions
  },

  computed: {
    unlocked () {
      return this.$store.state[this.namespace].unlocked;
    },

    lock_unlock_str () {
      return this.unlocked ? "lock" : "unlock";
    },

    pass_button_action () {
      return this.pass_unlocked ? "pass" : "unlock_pass";
    },

    pass_unlocked () {
      return this.$store.state[this.namespace].pass_unlocked;
    },

    asker () {
      return this.$store.state[this.namespace].asker;
    },

    giver () {
      return this.$store.state[this.namespace].giver;
    },

    trading () {
      return this.$store.state[this.namespace].trading;
    },

    alt_play_button_str () {
      return this.$store.getters[`${this.namespace}/alt_play_button_str`];
    }
  }
};
</script>

<style scoped>
.v-btn {
  text-transform: lowercase !important;
}
</style>
