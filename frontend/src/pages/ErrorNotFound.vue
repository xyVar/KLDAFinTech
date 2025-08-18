<template>
  <div class="fullscreen bg-blue text-white text-center q-pa-md flex flex-center">
    <div>
      <div style="font-size: 30vh">404</div>
      <div class="text-h2">Oops. Nothing here...</div>

      <q-btn class="q-mt-xl"
             color="white"
             text-color="blue"
             rounded
             flat
             icon="keyboard_return"
             label="Go Back"
             @click="$router.go(-1)" />
    </div>
  </div>
</template>

<script setup></script>

<style scoped></style>
