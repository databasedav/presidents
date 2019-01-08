<template>
  <span>
    {{ message }}
  </span>
</template>

<script>
export default {
  computed: {
    ...mapState({
      message: 'message'
    }),
  },
}
</script>

<style>

</style>
