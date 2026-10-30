import 'package:flutter/material.dart';
import 'package:flutter_hbb/common.dart';
import 'package:flutter_hbb/models/platform_model.dart';
import 'package:get/get.dart';

const String kTkNamespaceOption = 'tk-namespace';

bool isTkTechVariant() =>
    bind.mainGetHardOption(key: 'tk-variant') == 'tech';

// The stored token is never read back into the UI; only whether one is set.
class TkNamespaceCard extends StatefulWidget {
  const TkNamespaceCard({Key? key}) : super(key: key);

  @override
  State<TkNamespaceCard> createState() => _TkNamespaceCardState();
}

class _TkNamespaceCardState extends State<TkNamespaceCard> {
  final TextEditingController _controller = TextEditingController();
  bool _hasToken =
      bind.mainGetLocalOption(key: kTkNamespaceOption).isNotEmpty;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _save(String value) async {
    await bind.mainSetLocalOption(key: kTkNamespaceOption, value: value);
    _controller.clear();
    setState(() => _hasToken = value.isNotEmpty);
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Flexible(
          child: SizedBox(
            width: 540,
            child: Card(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Namespace token', style: TextStyle(fontSize: 20))
                      .marginOnly(left: 15, top: 10, bottom: 10),
                  Text(_hasToken ? 'Token is set' : 'Token is not set')
                      .marginOnly(left: 15, bottom: 8),
                  TextField(
                    controller: _controller,
                    obscureText: true,
                    enableSuggestions: false,
                    autocorrect: false,
                    decoration: const InputDecoration(
                      hintText: 'Paste the token from the password manager',
                    ),
                  ).marginSymmetric(horizontal: 15),
                  Row(
                    children: [
                      ElevatedButton(
                        onPressed: () {
                          final value = _controller.text.trim();
                          if (value.isNotEmpty) _save(value);
                        },
                        child: Text(translate('Save')),
                      ),
                      const SizedBox(width: 8),
                      TextButton(
                        onPressed: _hasToken ? () => _save('') : null,
                        child: Text(translate('Clear')),
                      ),
                    ],
                  ).marginAll(15),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }
}
