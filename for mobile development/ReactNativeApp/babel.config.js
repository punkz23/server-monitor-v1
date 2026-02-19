module.exports = {
  presets: ['module:metro-react-native-babel-preset'],
  plugins: [
    // NOTE: This must be listed last per Reanimated docs
    'react-native-reanimated/plugin',
  ],
};
