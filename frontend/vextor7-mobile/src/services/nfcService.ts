import NfcManager, { NfcTech, Ndef } from 'react-native-nfc-manager';

export const nfcService = {
  init: async () => {
    const supported = await NfcManager.isSupported();
    if (supported) {
      await NfcManager.start();
    }
    return supported;
  },

  readTag: async (): Promise<string | null> => {
    try {
      await NfcManager.requestTechnology(NfcTech.Ndef);
      const tag = await NfcManager.getTag();
      
      if (tag?.ndefMessage && tag.ndefMessage.length > 0) {
        const payload = tag.ndefMessage[0].payload;
        return Ndef.text.decodePayload(payload);
      }
      return null;
    } catch (ex) {
      console.warn(ex);
      return null;
    } finally {
      NfcManager.cancelTechnologyRequest();
    }
  },

  writeTag: async (data: string): Promise<boolean> => {
    try {
      await NfcManager.requestTechnology(NfcTech.Ndef);
      const bytes = Ndef.encodeMessage([Ndef.textRecord(data)]);
      if (bytes) {
        await NfcManager.ndefHandler.writeNdefMessage(bytes);
        return true;
      }
      return false;
    } catch (ex) {
      console.warn(ex);
      return false;
    } finally {
      NfcManager.cancelTechnologyRequest();
    }
  }
};